# Android Media

**Use when:** routing media or document picks, sharing app-owned `content` URIs, or implementing Media3 background playback at target SDK 37.

Required: declare Media3 through `assets/libs.versions.toml.template` (`media3` version ref, `media3-playback` bundle: `media3-exoplayer`, `media3-session`). Pin from [Media3 releases](https://developer.android.com/jetpack/androidx/releases/media3). Catalog routing: [dependencies.md → Media3](dependencies.md#media3).

Use [Picking media and documents](#picking-media-and-documents), [Sharing media and files](#sharing-media-and-files), and [Scoped storage and permissions](#scoped-storage-and-permissions) as indexes into [android-permissions.md](android-permissions.md), [android-security.md](android-security.md), and [android-notifications.md](android-notifications.md). Implement playback under [Background media playback hardening (API 37)](#background-media-playback-hardening-api-37).

Image loading: [android-graphics.md → Image Loading with Coil3](android-graphics.md). Camera, screen recording, partial screen share: [android-security.md](android-security.md). Playback notifications and PiP: [android-notifications.md](android-notifications.md).

## Table of Contents

1. [Picking media and documents](#picking-media-and-documents)
2. [Sharing media and files](#sharing-media-and-files)
3. [Scoped storage and permissions](#scoped-storage-and-permissions)
4. [Playback preloading (Media3)](#playback-preloading-media3)
5. [Background media playback hardening (API 37)](#background-media-playback-hardening-api-37)

## Picking media and documents

Use the table as an index only; contracts and samples sit in the linked rows.

| Need                                                                   | Route                                                                                                                                                           |
|------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Pick images or video without broad `READ_MEDIA_*` when UX allows       | [android-permissions.md → Photo Picker (Android 13+)](android-permissions.md#photo-picker-android-13) |
| Generic MIME or documents (`GetContent`, `OpenDocument`, multi-select) | [android-permissions.md → Requesting Runtime Permissions in Compose](android-permissions.md#requesting-runtime-permissions-in-compose)              |

## Sharing media and files

| Need                                                       | Route                                                                                                                                                  |
|------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|
| `content://` backed by app files for another package       | [android-security.md → FileProvider for Secure File Sharing](android-security.md#fileprovider-for-secure-file-sharing)                     |
| `ACTION_SEND` / `ACTION_SEND_MULTIPLE` with `content` URIs | [android-security.md → URI grants on outbound intents](android-security.md#uri-grants-on-outbound-intents) |
| System chooser UX for text or streams                      | [android-notifications.md → System sharesheet](android-notifications.md#system-sharesheet)                                                 |

## Scoped storage and permissions

**Use:** [android-permissions.md](android-permissions.md) for scoped-storage capability matrix; [android-security.md](android-security.md) for outbound `content` trust boundaries and profile edge cases.

## Playback preloading (Media3)

**Use when:** the next queue item must start with less startup latency (feeds, playlists, autoplay chains).

**Forbidden:** preloading entire catalogs or unbounded URL lists; cap concurrent preload windows.

Required: use Media3 `PreloadManager` (and related APIs) per official guides - [Introducing preloading with Media3 - Part 1](https://developer.android.com/blog/posts/elevating-media-playback-introducing-preloading-with-media3-part-1), [PreloadManager deep dive - Part 2](https://developer.android.com/blog/posts/elevating-media-playback-a-deep-dive-into-media3-s-preload-manager-part-2). Wire the same `Player` / `MediaSession` stack as [Background media playback hardening (API 37)](#background-media-playback-hardening-api-37).

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
- Holding a manual `PowerManager.WakeLock` alongside `MediaSessionService`. [android-performance.md → Excessive partial wake locks](android-performance.md#excessive-partial-wake-locks-play-vitals-core-metric).

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
