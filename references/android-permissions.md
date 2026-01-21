# Android Runtime Permissions

Practical, Compose-first patterns for requesting permissions in Android apps. This guide follows modern Android best practices and our modular architecture.

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
Use for camera capture and media access.

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

Use Accompanist Permissions with Compose-first APIs.

```kotlin
dependencies {
    implementation(libs.accompanist.permissions)
}
```

### Single Permission (CameraAccess)

```kotlin
@OptIn(ExperimentalPermissionsApi::class)
@Composable
fun CameraAccess(
    onOpenCamera: () -> Unit,
    modifier: Modifier = Modifier
) {
    val permissionState = rememberPermissionState(Manifest.permission.CAMERA)

    Button(
        modifier = modifier,
        onClick = {
            if (permissionState.status.isGranted) {
                onOpenCamera()
            } else {
                permissionState.launchPermissionRequest()
            }
        }
    ) {
        Text("Open Camera")
    }
}
```

### Multiple Permissions (PhotoAccess)

```kotlin
@OptIn(ExperimentalPermissionsApi::class)
@Composable
fun PhotoAccess(
    onOpenPicker: () -> Unit,
    onShowRationale: () -> Unit,
    modifier: Modifier = Modifier
) {
    val permissionsState = rememberMultiplePermissionsState(
        permissions = buildMediaPermissions()
    )

    Button(
        modifier = modifier,
        onClick = {
            when {
                permissionsState.allPermissionsGranted -> onOpenPicker()
                permissionsState.shouldShowRationale -> onShowRationale()
                else -> permissionsState.launchMultiplePermissionRequest()
            }
        }
    ) {
        Text("Choose Photo")
    }
}
```

## Rationale and "Don't Ask Again"

- Request permissions **contextually** (e.g., when the user taps "Open Camera").
- If the user denies and "Don't ask again" is selected, guide them to Settings.

```kotlin
@OptIn(ExperimentalPermissionsApi::class)
@Composable
fun CameraAccessGate(
    onOpenCamera: () -> Unit,
    onOpenSettings: () -> Unit
) {
    val permissionState = rememberPermissionState(Manifest.permission.CAMERA)

    when {
        permissionState.status.isGranted -> onOpenCamera()
        permissionState.status.shouldShowRationale -> PermissionRationaleCard(
            onAllow = { permissionState.launchPermissionRequest() }
        )
        permissionState.status.isPermanentlyDenied() -> PermissionSettingsPrompt(
            onOpenSettings = onOpenSettings
        )
        else -> PermissionRequestCard(
            onRequest = { permissionState.launchPermissionRequest() }
        )
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

Helper for "Don't ask again":

```kotlin
@OptIn(ExperimentalPermissionsApi::class)
fun PermissionStatus.isPermanentlyDenied(): Boolean {
    return this is PermissionStatus.Denied && !shouldShowRationale
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
