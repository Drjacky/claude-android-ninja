# Android Media

Required: at target SDK 37, every background media playback session - audio or video - runs inside a Media3 `MediaSessionService` with a `mediaPlayback` foreground service type. Standalone `MediaPlayer` / `AudioTrack` background audio is silently dropped and `requestAudioFocus()` returns `AUDIOFOCUS_REQUEST_FAILED`.

Scope: Media3 playback hardening. Image loading -> [android-graphics.md → Image Loading with Coil3](/references/android-graphics.md). Media-style notifications and PiP -> [android-notifications.md](/references/android-notifications.md). Camera capture, screen recording, partial screen sharing -> [android-security.md](/references/android-security.md).

## Background media playback hardening (API 37)

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
- Holding a manual `PowerManager.WakeLock` alongside `MediaSessionService`. See [android-performance.md → Excessive partial wake locks](/references/android-performance.md#excessive-partial-wake-locks-play-vitals-core-metric).

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

## Cross-references

- [android-performance.md → Excessive partial wake locks](/references/android-performance.md#excessive-partial-wake-locks-play-vitals-core-metric) - the wake-lock interaction rule.
- [android-permissions.md](/references/android-permissions.md) - manifest permission declaration pattern.
- [android-notifications.md](/references/android-notifications.md) - playback notification styling and channel rules.
