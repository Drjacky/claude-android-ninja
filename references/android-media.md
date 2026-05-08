# Android Media

**Use when:** routing media or document picks, sharing app-owned `content` URIs, or implementing Media3 background playback at target SDK 37.

Use [Picking media and documents](#picking-media-and-documents), [Sharing media and files](#sharing-media-and-files), and [Scoped storage and permissions](#scoped-storage-and-permissions) as indexes into [android-permissions.md](/references/android-permissions.md), [android-security.md](/references/android-security.md), and [android-notifications.md](/references/android-notifications.md). Implement playback under [Background media playback hardening (API 37)](#background-media-playback-hardening-api-37).

Image loading: [android-graphics.md → Image Loading with Coil3](/references/android-graphics.md). Camera, screen recording, partial screen share: [android-security.md](/references/android-security.md). Playback notifications and PiP: [android-notifications.md](/references/android-notifications.md).

## Table of Contents

1. [Picking media and documents](#picking-media-and-documents)
2. [Sharing media and files](#sharing-media-and-files)
3. [Scoped storage and permissions](#scoped-storage-and-permissions)
4. [Background media playback hardening (API 37)](#background-media-playback-hardening-api-37)

## Picking media and documents

Use the table as an index only; contracts and samples sit in the linked rows.

| Need                                                                   | Route                                                                                                                                                           |
|------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Pick images or video without broad `READ_MEDIA_*` when UX allows       | [android-permissions.md → Photo Picker (Preferred for Media on Android 13+)](/references/android-permissions.md#photo-picker-preferred-for-media-on-android-13) |
| Generic MIME or documents (`GetContent`, `OpenDocument`, multi-select) | [android-permissions.md → Requesting Runtime Permissions in Compose](/references/android-permissions.md#requesting-runtime-permissions-in-compose)              |

## Sharing media and files

| Need                                                       | Route                                                                                                                                                  |
|------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|
| `content://` backed by app files for another package       | [android-security.md → FileProvider for Secure File Sharing](/references/android-security.md#fileprovider-for-secure-file-sharing)                     |
| `ACTION_SEND` / `ACTION_SEND_MULTIPLE` with `content` URIs | [android-security.md → Forward-compatible URI grants (Android 18 prep)](/references/android-security.md#forward-compatible-uri-grants-android-18-prep) |
| System chooser UX for text or streams                      | [android-notifications.md → System sharesheet](/references/android-notifications.md#system-sharesheet)                                                 |

## Scoped storage and permissions

**Use:** [android-permissions.md](/references/android-permissions.md) for scoped-storage capability matrix; [android-security.md](/references/android-security.md) for outbound `content` trust boundaries and profile edge cases.

## Background media playback hardening (API 37)

Required: at target SDK 37, every background media playback session - audio or video - runs inside a Media3 `MediaSessionService` with a `mediaPlayback` foreground service type. Standalone `MediaPlayer` / `AudioTrack` background audio is silently dropped and `requestAudioFocus()` returns `AUDIOFOCUS_REQUEST_FAILED`.

The same rule covers audio-only, video-only, and audio-with-video playback. The audio-focus enforcement bullet applies only when audio is playing.

Required:
- Subclass `MediaSessionService` and build a `MediaSession` from a Media3 `Player` (`ExoPlayer` is the default; works for audio, video, or both).
- Set `android:foregroundServiceType="mediaPlayback"` on the service in the manifest.
- Declare `android.permission.FOREGROUND_SERVICE` and `android.permission.FOREGROUND_SERVICE_MEDIA_PLAYBACK`.
- Release the `MediaSession` and the underlying `Player` in `onDestroy()`. A leaked session leaves an undismissible playback notification.
- Stop the service when playback ends: `Player.STATE_ENDED` -> `stopSelf()`.

Forbidden:
- Standalone `MediaPlayer`, `AudioTrack`, or raw `ExoPlayer` background playback without a `MediaSession` at target 37.
- `requestAudioFocus()` from a service that has no `MediaSession` while audio is active. The call returns `AUDIOFOCUS_REQUEST_FAILED` at target 37 with no exception.
- Holding a manual `PowerManager.WakeLock` alongside `MediaSessionService`. [android-performance.md → Excessive partial wake locks](/references/android-performance.md#excessive-partial-wake-locks-play-vitals-core-metric).

### Manifest

```xml
<uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
<uses-permission android:name="android.permission.FOREGROUND_SERVICE_MEDIA_PLAYBACK" />

<application ...>
    <service
        android:name=".playback.PlaybackService"
        android:exported="false"
        android:foregroundServiceType="mediaPlayback">
        <intent-filter>
            <action android:name="androidx.media3.session.MediaSessionService" />
        </intent-filter>
    </service>
</application>
```

### Service skeleton

```kotlin
@OptIn(UnstableApi::class)
class PlaybackService : MediaSessionService() {

    private var mediaSession: MediaSession? = null

    private val playerListener = object : Player.Listener {
        override fun onPlaybackStateChanged(state: Int) {
            if (state == Player.STATE_ENDED) stopSelf()
        }
    }

    override fun onCreate() {
        super.onCreate()
        val player = ExoPlayer.Builder(this).build().apply {
            addListener(playerListener)
        }
        mediaSession = MediaSession.Builder(this, player).build()
    }

    override fun onGetSession(
        controllerInfo: MediaSession.ControllerInfo,
    ): MediaSession? = mediaSession

    override fun onDestroy() {
        mediaSession?.run {
            player.removeListener(playerListener)
            player.release()
            release()
        }
        mediaSession = null
        super.onDestroy()
    }
}
```
